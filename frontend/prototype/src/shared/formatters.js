export const escapeHtml = (value = '') => String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[char]);

const number = new Intl.NumberFormat('vi-VN', { maximumFractionDigits: 2 });
export const money = (value) => value === null ? 'Chưa đủ dữ liệu' : number.format(value / 1e9);
export const fullMoney = (value) => value === null ? 'Chưa đủ dữ liệu' : `${new Intl.NumberFormat('vi-VN').format(value)} ₫`;
export const percent = (value) => value === null ? 'Chưa xác định' : `${number.format(value * 100)}%`;
export const date = (value) => value ? new Intl.DateTimeFormat('vi-VN').format(new Date(`${value}T00:00:00`)) : 'Chưa có ngày';
export const time = (value) => new Intl.DateTimeFormat('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }).format(new Date(value));

export function safeSum(values) {
    if (values.some((value) => value === null || value === undefined)) return null;
    return values.reduce((sum, value) => {
        if (!Number.isSafeInteger(value) || !Number.isSafeInteger(sum + value)) throw new RangeError('Giá trị tiền vượt giới hạn an toàn.');
        return sum + value;
    }, 0);
}

export const ratio = (numerator, denominator) => numerator === null || denominator === null || denominator === 0 ? null : numerator / denominator;
export const subtract = (a, b) => a === null || b === null ? null : safeSum([a, -b]);
export const normalize = (value) => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'd').replace(/Đ/g, 'D').toLowerCase();
