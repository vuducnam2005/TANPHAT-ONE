// Entirely synthetic fixtures. No financial values are copied from the NAS workbook.
const billion = (value) => Math.round(value * 1e9);
export const projects = [
    { id: 'dong-thanh', code: 'DA-2601', name: 'Hạ tầng khu đô thị Đông Thành', investor: 'Ban quản lý dự án Đông Thành (mẫu)', location: 'Đồng Nai', phase: 'Đang triển khai', manager: 'Phòng Kế hoạch Kinh doanh', start: '2026-01-15' },
    { id: 'an-binh', code: 'DA-2602', name: 'Tuyến kết nối An Bình', investor: 'Ban quản lý hạ tầng An Bình (mẫu)', location: 'Bình Dương', phase: 'Đang triển khai', manager: 'Phòng Kế hoạch Kinh doanh', start: '2026-03-10' },
    { id: 'nam-son', code: 'DA-2603', name: 'Quy hoạch khu dân cư Nam Sơn', investor: 'Chưa cập nhật (mẫu)', location: 'Đồng Nai', phase: 'Chuẩn bị', manager: 'Phòng Kế hoạch Kinh doanh', start: '2026-10-01' },
];

const definitions = [
    { id: 'survey', side: 'investor', name: 'Khảo sát xây dựng', contract: 10, replacement: 11.4, production: 9.1, accepted: 7.9, paid: 6.4, retention: .395 },
    { id: 'basic', side: 'investor', name: 'Thiết kế cơ sở', contract: 8, production: 6.2, accepted: 4.8, paid: 5.6, retention: .24 },
    { id: 'technical', side: 'investor', name: 'Thiết kế kỹ thuật', contract: 9, production: null, accepted: 3, paid: 2, retention: .15 },
    { id: 'dept-design', side: 'contractor', name: 'Phòng Thiết kế hạ tầng', work: 'Thiết kế hạ tầng', type: 'Khoán nội bộ', level: 1, contract: 8.4, production: 5.7, accepted: 4.8, paid: 3.6 },
    { id: 'geo', side: 'contractor', name: 'Đơn vị Địa hình Việt (mẫu)', work: 'Khảo sát địa hình', type: 'Thầu phụ trực tiếp', level: 1, contract: 6.6, production: 5.8, accepted: 5.2, paid: 4.1 },
    { id: 'structure', side: 'contractor', name: 'Đơn vị Kết cấu Nam (mẫu)', work: 'Thiết kế kết cấu', type: 'Thầu phụ trực tiếp', level: 1, contract: 4.2, production: 3.1, accepted: 2.6, paid: 2.9 },
    { id: 'roads', side: 'contractor', name: 'Nhóm Thiết kế đường (mẫu)', work: 'Thiết kế đường giao thông', type: 'Thầu phụ của phòng', level: 2, parentId: 'dept-design', contract: 5.2, production: 3.3, accepted: 2.8, paid: 2 },
    { id: 'drainage', side: 'contractor', name: 'Nhóm Cấp thoát nước (mẫu)', work: 'Thiết kế thoát nước', type: 'Thầu phụ của phòng', level: 2, parentId: 'dept-design', contract: 3.6, production: 2.1, accepted: 1.6, paid: 1.2 },
];

export function createFixtures() {
    const items = [];
    const transactions = [];
    for (const [projectIndex, project] of projects.slice(0, 2).entries()) {
        const factor = projectIndex ? .6 : 1;
        const templates = projectIndex ? definitions.filter((item) => !['technical', 'structure', 'drainage'].includes(item.id)) : definitions;
        for (const template of templates) {
            const { contract, replacement, production, accepted, paid, retention = 0, ...meta } = template;
            const item = { ...meta, projectId: project.id, productionKnown: production !== null };
            items.push(item);
            const amount = (value) => billion(value * factor);
            let sourceRow = transactions.length + 1;
            const add = (rootId, bookingDate, description, amounts, extra = {}) => transactions.push({
                projectId: project.id, side: item.side, itemId: item.id, rootId: `${item.id}-${rootId}`, sequence: 1, operation: 'write',
                sourceRow: sourceRow++, date: bookingDate, description, contractOriginal: 0, contractReplacement: 0,
                production: 0, accepted: 0, paid: 0, retention: 0, ...amounts, ...extra,
            });
            add('contract', '2026-03-15', 'Ký hợp đồng / giao khoán ban đầu', { contractOriginal: amount(contract) });
            if (replacement) add('appendix', '2026-06-18', 'Phụ lục thay thế toàn bộ giá trị hợp đồng', { contractReplacement: amount(replacement) });
            add('work-1', '2026-07-10', 'Khối lượng và nghiệm thu đợt 1', { production: production === null ? 0 : amount(production * .4), accepted: amount(accepted * .4), retention: amount(retention * .4) });
            add('payment-1', '2026-07-28', 'Thanh toán đợt 1', { paid: amount(paid * .45) });
            // Version 2 replaces version 1. Sequence 10 is intentional for numeric-order testing.
            add('work-2', '2026-09-20', 'Nghiệm thu đợt 2 — bản trước cập nhật', { production: production === null ? 0 : amount(production * .5), accepted: amount(accepted * .5) });
            add('work-2', '2026-09-22', 'Khối lượng và nghiệm thu đợt 2 đã cập nhật', { production: production === null ? 0 : amount(production * .6), accepted: amount(accepted * .6), retention: amount(retention * .6) }, { sequence: 10 });
            add('payment-2', '2026-10-12', 'Thanh toán đợt 2 / tạm ứng', { paid: amount(paid * .55) });
            if (item.id === 'survey') {
                add('cancelled', '2026-10-15', 'Bản nháp thanh toán đã hủy', { paid: amount(.3) });
                add('cancelled', '2026-10-16', 'Hủy bản nháp thanh toán', {}, { sequence: 2, operation: 'delete' });
            }
        }
    }
    return { projects: structuredClone(projects), items, transactions };
}
