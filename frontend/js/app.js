let cart = [];

const API_URL = "http://localhost:8000";
let productsDB = []; // Danh sách sản phẩm toàn cục
let invoicesData = []; // Danh sách hóa đơn toàn cục
let snackbarTimeout;

// --- Thiết lập giao diện khi tải trang ---
document.addEventListener('DOMContentLoaded', () => {
    renderProducts();
});

// Chuyển Tab (Dashboard / POS / Inventory / Invoices)
function switchTab(tabId, element) {
    document.querySelectorAll('.view-section').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));

    document.getElementById(`${tabId}-view`).classList.add('active');
    if (element) {
        element.classList.add('active');
    }

    if (tabId === 'inventory') loadInventory();
    if (tabId === 'invoices') loadInvoices();
    if (tabId === 'pos') renderProducts(); // Refresh kho khi vào lại POS
}

// Render dữ liệu mặt hàng ra Lưới (Grid) TỪ DATABASE MỚI NHẤT
async function renderProducts() {
    const grid = document.getElementById('products-grid');
    grid.innerHTML = '<p style="padding: 20px; color: #5f6368;">Đang tải danh sách món...</p>';

    try {
        const response = await fetch(`${API_URL}/inventory`);
        if (!response.ok) throw new Error("Fetch failed");
        productsDB = await response.json();

        grid.innerHTML = '';
        productsDB.forEach(product => {
            const div = document.createElement('div');

            // Xử lý Hết hàng
            if (product.stock_quantity <= 0) {
                div.className = 'product-card elevation-1';
                div.style.opacity = '0.5';
                div.onclick = () => showSnackbar(`Sản phẩm ${product.name} đã hết hàng!`);
            } else {
                div.className = 'product-card elevation-1';
                div.onclick = () => addToCart(product);
            }

            // Icon minh hoạ tạm (Dựa trên SKU)
            let icon = 'inventory_2';
            if (product.sku.includes("FOO") || product.sku.includes("SNC")) icon = 'fastfood';
            if (product.sku.includes("DRK")) icon = 'local_cafe';

            div.innerHTML = `
                <div class="product-img">
                    <span class="material-symbols-rounded">${icon}</span>
                </div>
                <div class="product-info">
                    <div class="product-name" title="${product.name}">${product.name}</div>
                    <div class="product-price">${formatCurrency(product.price)}</div>
                    <div style="font-size: 11px; margin-top: 4px; font-weight: bold; color: ${product.stock_quantity > 0 ? '#4caf50' : '#e53935'};">Kho còn: ${product.stock_quantity}</div>
                </div>
            `;
            grid.appendChild(div);
        });
    } catch (e) {
        grid.innerHTML = '<p style="padding: 20px; color: #d32f2f;">Lỗi kết nối Backend. Chưa chạy uvicorn?</p>';
        showSnackbar("Lỗi lấy dữ liệu món ăn!");
    }
}

// --- Logic Hệ Thống Giỏ Hàng ---
function addToCart(product) {
    const existingItem = cart.find(item => item.product_id === product.id);
    if (existingItem) {
        existingItem.quantity += 1;
    } else {
        cart.push({
            product_id: product.id,
            name: product.name,
            price: product.price,
            quantity: 1
        });
    }
    renderCart();

    // Rung hiệu ứng nhỏ khi thêm
    showSnackbar(`Đã thêm ${product.name} vào giỏ`);
}

function updateQuantity(productId, delta) {
    const itemIndex = cart.findIndex(item => item.product_id === productId);
    if (itemIndex > -1) {
        cart[itemIndex].quantity += delta;
        if (cart[itemIndex].quantity <= 0) {
            cart.splice(itemIndex, 1);
        }
        renderCart();
    }
}

function clearCart() {
    if (cart.length > 0 && confirm("Bạn có chắc chắn hủy toàn bộ giỏ hàng?")) {
        cart = [];
        renderCart();
    }
}

function renderCart() {
    const cartItemsEl = document.getElementById('cart-items');

    if (cart.length === 0) {
        cartItemsEl.innerHTML = `
            <div class="empty-cart-msg">
                <span class="material-symbols-rounded" style="font-size: 48px; opacity: 0.3;">shopping_basket</span>
                <p style="margin-top: 10px;">Chưa chọn sản phẩm nào</p>
            </div>`;
        updateSummary(0);
        return;
    }

    cartItemsEl.innerHTML = '';
    let subtotal = 0;

    cart.forEach(item => {
        subtotal += item.price * item.quantity;
        const el = document.createElement('div');
        el.className = 'cart-item elevation-1';
        el.innerHTML = `
            <div class="item-visual"><span class="material-symbols-rounded" style="color:#9e9e9e;">receipt_long</span></div>
            <div class="item-details">
                <div class="item-name">${item.name}</div>
                <div class="item-price">${formatCurrency(item.price)}</div>
            </div>
            <div class="item-actions">
                <button class="qty-btn" onclick="updateQuantity(${item.product_id}, -1)">-</button>
                <span style="font-weight:700; width: 24px; text-align: center; color: var(--md-text-primary);">${item.quantity}</span>
                <button class="qty-btn" onclick="updateQuantity(${item.product_id}, 1)">+</button>
            </div>
        `;
        cartItemsEl.appendChild(el);
    });

    updateSummary(subtotal);
}

function updateSummary(subtotal) {
    const taxRate = 0.1; // Khung Thuế 10% VAT
    const tax = subtotal * taxRate;
    const total = subtotal + tax;

    document.getElementById('summary-subtotal').innerText = formatCurrency(subtotal);
    document.getElementById('summary-tax').innerText = formatCurrency(tax);
    document.getElementById('summary-total').innerText = formatCurrency(total);
}

// Hàm Format định dạng Tiền VND
function formatCurrency(amount) {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount);
}

// --- Gọi API Thanh Toán gửi xuống DB ---
async function checkout() {
    if (cart.length === 0) {
        showSnackbar("Không thể thanh toán, giỏ hàng đang trống!");
        return;
    }

    // Soạn Payload JSON Map dữ liệu để bẩy Pydantic OrderCreate Schema ở Backend
    const payload = {
        customer_id: null, // Mua nhanh vãng lai nên không gán User ID
        items: cart.map(item => ({
            product_id: item.product_id,
            quantity: item.quantity
        })),
        discount: 0,
        tax_rate: 0.1,
        payment_method: "Cash"
    };

    try {
        // Thực thi gọi API vào core ứng dụng Python đã dựng
        const response = await fetch(`${API_URL}/orders`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (response.ok) {
            const result = await response.json();
            showSnackbar(`🎉 Thanh toán Thành Công! Tạo Đơn Số #${result.id}`);
            cart = [];
            renderCart();
            renderProducts(); // Tự động kéo lại tồn kho mới nhất
        } else {
            // Hiển thị Lỗi nghiệp vụ từ Server (VD: Không đủ tồn kho, hoặc chưa setup DB)
            const errorData = await response.json();
            showSnackbar(`Lỗi Nghiệp vụ: ${errorData.detail}`);
            console.error("Backend Error Detail:", errorData);
        }
    } catch (error) {
        console.error("Network Error:", error);
        showSnackbar("Báo lỗi kết nối mạng! Backend Python đứt mạng hoặc chưa bật CORS.");
    }
}

// Hệ thống cảnh báo tự động Toast (Snackbar) kiểu Material
function showSnackbar(message) {
    const snackbar = document.getElementById("snackbar");
    snackbar.innerText = message;
    snackbar.className = "snackbar elevation-3 show";
    
    // Clear timeout cũ nếu bấm liên tục
    clearTimeout(snackbarTimeout);
    snackbarTimeout = setTimeout(function () { snackbar.className = snackbar.className.replace("show", ""); }, 3500);
}

// --- Gọi API Lấy Tồn Kho ---
async function loadInventory(isManualRefresh = false) {
    try {
        const response = await fetch(`${API_URL}/inventory?t=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) throw new Error("Fetch failed");
        const data = await response.json();

        const tbody = document.getElementById('inventory-tbody');
        tbody.innerHTML = '';
        data.forEach(item => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td style="padding: 16px; border-bottom: 1px solid #e0e0e0; font-weight: 500;">${item.sku}</td>
                <td style="padding: 16px; border-bottom: 1px solid #e0e0e0;">${item.name}</td>
                <td style="padding: 16px; border-bottom: 1px solid #e0e0e0;">${formatCurrency(item.price)}</td>
                <td style="padding: 16px; border-bottom: 1px solid #e0e0e0;">
                    <span style="font-weight: bold; color: ${item.stock_quantity < item.min_stock_level ? '#d32f2f' : 'inherit'};">${item.stock_quantity}</span>
                </td>
                <td style="padding: 16px; border-bottom: 1px solid #e0e0e0;">
                    <button class="md-button" style="padding: 6px 16px; font-size: 13px; background: rgba(98,0,234,0.1); color: var(--md-primary);" 
                            onclick="restockProduct(${item.id}, '${item.name}')">
                        Nhập Hàng
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });

        if (isManualRefresh) {
            showSnackbar("Đã làm mới Tồn Kho!");
        }
    } catch (e) {
        showSnackbar("Lỗi tải Tồn Kho!");
    }
}

// --- Gọi API Lấy Hóa Đơn ---
async function loadInvoices(isManualRefresh = false) {
    try {
        const response = await fetch(`${API_URL}/invoices?t=${Date.now()}`, { cache: 'no-store' });
        if (!response.ok) throw new Error("Fetch failed");
        invoicesData = await response.json();

        const tbody = document.getElementById('invoices-tbody');
        tbody.innerHTML = '';
        invoicesData.forEach(order => {
            const dateStr = new Date(order.created_at).toLocaleString('vi-VN');
            
            const tr = document.createElement('tr');
            tr.style.cursor = 'pointer';
            tr.className = 'hoverable-row';
            tr.onclick = () => showInvoiceDetails(order.id);
            tr.innerHTML = `
                <td style="padding: 16px; border-bottom: 1px solid #e0e0e0; font-weight: 500;">#${order.id}</td>
                <td style="padding: 16px; border-bottom: 1px solid #e0e0e0; color: #5f6368;">${dateStr}</td>
                <td style="padding: 16px; border-bottom: 1px solid #e0e0e0;">... ${order.items.length} mặt hàng</td>
                <td style="padding: 16px; border-bottom: 1px solid #e0e0e0; font-weight: bold; color: var(--md-primary);">${formatCurrency(order.final_amount)}</td>
                <td style="padding: 16px; border-bottom: 1px solid #e0e0e0;">
                    <span class="md-chip" style="background: #e8f5e9; color: #2e7d32; cursor: pointer;">Thành Công</span>
                </td>
            `;
            tbody.appendChild(tr);
        });

        if (isManualRefresh) {
            showSnackbar("Đã làm mới Lịch Sử Hóa Đơn!");
        }
    } catch (e) {
        showSnackbar("Lỗi tải Hóa Đơn!");
    }
}

// --- Gọi API Nhập kho ---
async function restockProduct(productId, productName) {
    const qtyStr = prompt(`Nhập số lượng hàng mới về cho [${productName}]:`, "10");
    if (qtyStr === null) return; // Kế toán ấn Cancel

    const qty = parseInt(qtyStr, 10);
    if (isNaN(qty) || qty <= 0) {
        showSnackbar("Số lượng không hợp lệ!");
        return;
    }

    try {
        const response = await fetch(`${API_URL}/inventory/${productId}/restock`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ quantity: qty })
        });

        if (response.ok) {
            showSnackbar(`Đã nhập thêm +${qty} cho sản phẩm ${productName}!`);
            loadInventory(); // Reload bảng
        } else {
            const err = await response.json();
            showSnackbar(`Lỗi: ${err.detail}`);
        }
    } catch (e) {
        showSnackbar("Lỗi kết nối khi nhập hàng!");
    }
}

// --- Gọi API Xóa toàn bộ hóa đơn ---
async function clearAllInvoices() {
    if(!confirm("⚠️ CẢNH BÁO: Bạn có chắc chắn muốn xóa vĩnh viễn toàn bộ lịch sử hóa đơn không? Hành động này không thể hoàn tác!")) return;
    
    try {
        const response = await fetch(`${API_URL}/invoices/clear`, { method: 'DELETE' });
        if (!response.ok) throw new Error("Delete failed");
        showSnackbar("🗑 Đã xóa toàn bộ lịch sử hóa đơn!");
        loadInvoices(); // Tải lại bảng để hiển thị dữ liệu trống
    } catch(e) {
        showSnackbar("Lỗi khi xóa hóa đơn!");
    }
}

// --- Modal Thêm Mặt Hàng Logic ---
function openAddProductModal() {
    document.getElementById('new-product-name').value = '';
    document.getElementById('new-product-price').value = '';
    document.getElementById('new-product-quantity').value = '';
    document.getElementById('add-product-modal').classList.add('show');
}

function closeAddProductModal() {
    document.getElementById('add-product-modal').classList.remove('show');
}

async function submitNewProduct() {
    const name = document.getElementById('new-product-name').value.trim();
    const priceStr = document.getElementById('new-product-price').value;
    const quantityStr = document.getElementById('new-product-quantity').value;
    
    if (!name || !priceStr || !quantityStr) {
        showSnackbar("Vui lòng điền đầy đủ thông tin mặt hàng!");
        return;
    }
    
    const price = parseFloat(priceStr);
    const quantity = parseInt(quantityStr, 10);
    
    if (price <= 0 || quantity < 0) {
        showSnackbar("Giá và số lượng phải hợp lệ!");
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/products`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                price: price,
                stock_quantity: quantity
            })
        });
        
        if (response.ok) {
            showSnackbar(`🎉 Đã tạo mặt hàng [${name}] thành công!`);
            closeAddProductModal();
            loadInventory();   // Update lại bảng kho
            renderProducts();  // Update lại danh sách POS
        } else {
            const err = await response.json();
            showSnackbar(`Lỗi: ${err.detail}`);
        }
    } catch(e) {
        showSnackbar("Lỗi kết nối khi tạo mặt hàng!");
    }
}

// --- Chi tiết hóa đơn ---
function showInvoiceDetails(id) {
    const order = invoicesData.find(o => o.id === id);
    if (!order) return;

    document.getElementById('detail-invoice-id').innerText = `Chi Tiết Hóa Đơn #${order.id}`;
    document.getElementById('detail-invoice-date').innerText = `Ngày tạo: ${new Date(order.created_at).toLocaleString('vi-VN')}`;
    document.getElementById('detail-invoice-method').innerText = `Thanh toán: ${order.payment_method || 'Tiền mặt'}`;
    
    document.getElementById('detail-total-amount').innerText = formatCurrency(order.total_amount);
    document.getElementById('detail-discount').innerText = `- ${formatCurrency(order.discount)}`;
    document.getElementById('detail-final-amount').innerText = formatCurrency(order.final_amount);

    const itemsTbody = document.getElementById('detail-invoice-items');
    itemsTbody.innerHTML = '';

    order.items.forEach(item => {
        const product = productsDB.find(p => p.id === item.product_id);
        const name = product ? product.name : `SP #${item.product_id}`;
        
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td style="padding: 12px; border-bottom: 1px solid #eee;">${name}</td>
            <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right;">${formatCurrency(item.unit_price)}</td>
            <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: center;">${item.quantity}</td>
            <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right; font-weight: 500;">${formatCurrency(item.subtotal)}</td>
        `;
        itemsTbody.appendChild(tr);
    });

    document.getElementById('invoice-details-modal').classList.add('show');
}

function closeInvoiceDetailsModal() {
    document.getElementById('invoice-details-modal').classList.remove('show');
}
