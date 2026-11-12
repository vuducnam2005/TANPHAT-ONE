import { describe, expect, test } from '@odoo/hoot';
import { contains, defineModels, fields, models, mountView, onRpc, patchWithCleanup } from '@web/../tests/web_test_helpers';
import { defineMailModels } from '@mail/../tests/mail_test_helpers';
import { ProjectPerspective } from '@tp_kd_workspace/project/perspective';
import { browser } from '@web/core/browser/browser';
import { session } from '@web/session';
import { user } from '@web/core/user';

class PerspectiveMock extends models.Model {
    _name='tp.project.perspective';
    name=fields.Char();
    _records=[{id:1,name:'Synthetic'}];
}
defineModels([PerspectiveMock]);
defineMailModels();
const payload=()=>({projects:[{id:42,code:'DA42',name:'Synthetic project'}],project_count:1,counts:[],rows:[],total:0});
const mount=()=>mountView({type:'form',resModel:'tp.project.perspective',resId:1,
    arch:'<form js_class="tp_project_perspective"><sheet/></form>'});

describe('KD-PROJECT-RESTRUCTURE-001 perspectives',()=>{
    test('project selection is shared across modes but isolated by database and actor',async()=>{
        patchWithCleanup(session,{db:'kdproject_hoot'});
        patchWithCleanup(user,{userId:817});
        const calls=[];
        onRpc('get_perspective',({args})=>{calls.push(args);return payload();});
        await mount();
        await contains('#tp_current_project').select('42');
        expect(calls.at(-1)[1]).toBe(42);
        expect(browser.sessionStorage.getItem('tp-kd-current-project:kdproject_hoot:817')).toBe('42');
        expect(browser.sessionStorage.getItem('tp-kd-current-project:kdproject_hoot:818')).toBe(null);
    });
    test('pagination resets offset for another project and empty count reads zero',async()=>{
        browser.sessionStorage.clear();
        const calls=[];
        onRpc('get_perspective',({args})=>{calls.push(args);return payload();});
        await mount();
        expect('.tp_project_pager').toHaveText(/0–0 \/ 0/);
        await contains('#tp_project_page_size').select('50');
        expect(calls.at(-1).slice(2)).toEqual([50,0]);
        await contains('#tp_current_project').select('42');
        expect(calls.at(-1)).toEqual(['management',42,50,0]);
    });
    test('task deadline and native progress have readable dates, meaning and tone',async()=>{
        browser.sessionStorage.clear();
        onRpc('get_perspective',()=>({...payload(),total:1,rows:[{id:8,name:'Synthetic task',project:'Synthetic project',owner:'Synthetic owner',deadline:'2026-11-09 03:00:00',state_key:'1_done',state:'Done',output:'Synthetic output'}]}));
        await mount();
        expect('.tp_project_state').toHaveText('Hoàn tất công việc');
        expect('.tp_project_state').toHaveClass('tp_kd_tone_success');
        expect('.tp_project_table tbody tr td:nth-child(4)').toHaveText(/09\/11\/2026 \d{2}:\d{2}/);
    });
    test('late response cannot overwrite fresh data and an error drops old rows',async()=>{
        let release;
        const delayed=new Promise(resolve=>{release=resolve;});
        const controller={sequence:0,mode:'management',state:{project:false,limit:20,offset:0},orm:{call:async()=>delayed}};
        const old=ProjectPerspective.prototype.load.call(controller);
        controller.orm.call=async()=>({...payload(),project_count:9});
        await ProjectPerspective.prototype.load.call(controller);
        release({...payload(),project_count:2});
        await old;
        expect(controller.state.data.project_count).toBe(9);
        controller.orm.call=async()=>{throw new Error('Synthetic failure');};
        await ProjectPerspective.prototype.load.call(controller);
        expect(controller.state.data).toBe(null);
        expect(controller.state.busy).toBe(false);
        expect(controller.state.error).not.toBe('');
    });
});
