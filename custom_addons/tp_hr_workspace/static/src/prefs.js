import { proxy } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { user } from "@web/core/user";
import { session } from "@web/session";
export const HR_APP_XMLID = "tp_hr_workspace.menu_hr";
export const LAST_LEAF_KEY = "tp_hr_ui:last_leaf";
export const PAGE_SIZE_OPTIONS = [10, 20, 50, 100];
function identity() { return `${session.db || ''}:${user.userId || 0}:${user.activeCompanies?.map(c => c.id).join(',') || ''}:tp_hr`; }
function storageKey() { return `tp_hr_ui:v1:${identity()}`; }
export function defaults() { return {collapsed:false, density:'comfortable', motion:'auto', groups:null}; }
function sanitize(raw) {
    const value = defaults();
    if (!raw || typeof raw !== 'object') return value;
    if (typeof raw.collapsed === 'boolean') value.collapsed = raw.collapsed;
    if (['comfortable','compact'].includes(raw.density)) value.density = raw.density;
    if (['auto','reduced'].includes(raw.motion)) value.motion = raw.motion;
    if (Array.isArray(raw.groups)) value.groups = raw.groups.filter(g => typeof g === 'string').slice(0,30);
    return value;
}
function load() { try { return sanitize(JSON.parse(browser.localStorage.getItem(storageKey()) || 'null')); } catch { return defaults(); } }
export const hrPrefs = proxy(load());
export function savePrefs(changes={}) { Object.assign(hrPrefs,sanitize({...hrPrefs,...changes})); try { browser.localStorage.setItem(storageKey(),JSON.stringify(hrPrefs)); } catch { /* unavailable storage keeps this tab usable */ } }
export function resetPrefs() { try {browser.localStorage.removeItem(storageKey());} catch { /* unavailable */ } Object.assign(hrPrefs,defaults()); }
export function tablePageKey(model,action,view) { return `tp_hr_page:v2:${identity()}:${model}:${action || ''}:${view || ''}`; }
export function readPageSize(key) { try { const value=Number(browser.localStorage.getItem(key)); return PAGE_SIZE_OPTIONS.includes(value) ? value : 100; } catch {return 100;} }
export function writePageSize(key,value) { if (!PAGE_SIZE_OPTIONS.includes(value)) return; try {browser.localStorage.setItem(key,String(value));} catch { /* unavailable */ } }
export function fold(text) { return (text || '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/đ/g,'d').replace(/Đ/g,'D').toLowerCase().trim(); }
export function isModifiedClick(ev) {return ev.ctrlKey || ev.metaKey || ev.shiftKey || ev.altKey || ev.button !== 0;}
