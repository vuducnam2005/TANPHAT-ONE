import { renderOverview } from './pages/overview.js';
import { renderInvestor } from './pages/investor.js';
import { renderContractors } from './pages/contractors.js';
import { renderDetail } from './pages/detail.js';
import { loadSnapshot } from './repository.js';

export const planningBusiness = {
    id: 'planning-business',
    name: 'Kế hoạch Kinh doanh',
    load: loadSnapshot,
    pages: [
        { id: 'overview', name: 'Tổng quan', icon: 'overview', render: renderOverview },
        { id: 'investor', name: 'Chủ đầu tư', icon: 'building', render: renderInvestor },
        { id: 'contractors', name: 'Thầu phụ & giao khoán', icon: 'hierarchy', render: renderContractors },
        { id: 'detail', name: 'Chi tiết dự án', icon: 'document', render: renderDetail },
    ],
    initialState: { itemId: '', contractorId: '', level: '', search: '', sort: 'name', detailSide: 'all', entityId: '', from: '', to: '', transactionSearch: '', transactionTab: 'effective' },
};
