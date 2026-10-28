import { subsystems } from '../../shared/config/product';

export interface WorkspaceDefinition {
  id: string;
  name: string;
  shortName: string;
  description: string;
  routes: Array<{ label: string; path: string; icon: string }>;
}

export const planningBusinessWorkspace: WorkspaceDefinition = {
  id: 'planning-business',
  name: 'Kế hoạch Kinh doanh',
  shortName: 'KHKD',
  description: 'Dự án trong phạm vi được phân công.',
  routes: [
    { label: subsystems.projects.name, path: '/projects', icon: '▦' },
  ],
};
