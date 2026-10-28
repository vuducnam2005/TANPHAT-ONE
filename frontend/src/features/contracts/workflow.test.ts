import { describe, expect, it } from 'vitest';
import { ApiError } from '../../shared/api/client';
import type { ApiErrorBody, ContractLine } from '../../shared/api/types';
import { lineDrafts, lineInputs, needsReload, newLineDraft, normalizeDecimal, workflowErrorMessage } from './workflow';
import type { AmountDraft } from './workflow';

const error = (status: number, code: string, details: ApiErrorBody['error']['details'] = null) =>
  new ApiError(status, { error: { code, message: `server ${code}`, details }, meta: { request_id: 'r' } }, 'fallback');

const confirmed = (value: string): AmountDraft => ({ state: 'confirmed', value, taxBasis: 'excluding_tax' });
const draft = (scopeKey: string, amount: AmountDraft | null, original = amount) =>
  ({ scopeKey, name: 'Survey', amount, original, isNew: false });

describe('contract workflow helpers', () => {
  it('keeps decimal input as text and rejects negatives, exponents and grouping', () => {
    expect(normalizeDecimal(' 1500000 ')).toBe('1500000');
    expect(normalizeDecimal('12,50')).toBe('12.50');
    expect(normalizeDecimal('0.1')).toBe('0.1');
    for (const value of ['-1', '1e6', '1.000.000', '', 'abc', '0x10']) expect(normalizeDecimal(value)).toBeNull();
  });

  it('sends only edited amounts and never without the financial edit grant', () => {
    expect(lineInputs([draft(' L1 ', confirmed('200'), confirmed('100'))], false)).toEqual({ lines: [{ scope_key: 'L1', name: 'Survey' }] });
    expect(lineInputs([draft('L1', confirmed('100'))], true)).toEqual({ lines: [{ scope_key: 'L1', name: 'Survey' }] });
    expect(lineInputs([draft('L1', confirmed('100,0'), confirmed('100.0'))], true)).toEqual({ lines: [{ scope_key: 'L1', name: 'Survey' }] });
    expect(lineInputs([draft('L1', confirmed('120'), confirmed('100'))], true)).toEqual({
      lines: [{ scope_key: 'L1', name: 'Survey', amount: { state: 'confirmed', value: '120', tax_basis: 'excluding_tax' } }],
    });
  });

  it('sends a new or unconfirmed amount as null, never as zero', () => {
    const fresh = { ...newLineDraft(true), scopeKey: 'L9', name: 'New' };
    const unconfirmed = draft('L1', { state: 'unconfirmed', value: '999', taxBasis: 'unknown' }, confirmed('100'));
    expect(lineInputs([fresh, unconfirmed], true)).toEqual({ lines: [
      { scope_key: 'L9', name: 'New', amount: { state: 'unconfirmed', value: null, tax_basis: 'unknown' } },
      { scope_key: 'L1', name: 'Survey', amount: { state: 'unconfirmed', value: null, tax_basis: 'unknown' } },
    ] });
    expect(lineInputs([newLineDraft(false)], false)).toHaveProperty('error');
  });

  it('rejects duplicate or blank scope keys and invalid amounts before calling the server', () => {
    expect(lineInputs([draft('L1', null), draft('L1', null)], false)).toEqual({ error: 'Mã phạm vi L1 bị trùng.' });
    expect(lineInputs([draft(' ', null)], false)).toHaveProperty('error');
    expect(lineInputs([draft('L1', confirmed('-5'), confirmed('1'))], true)).toHaveProperty('error');
  });

  it('builds drafts from revision lines, with amounts only when they may be edited', () => {
    const line = {
      id: 1, sequence: 10, scope_key: 'L1', name: 'Survey', work_item: null, change_kind: 'original', previous_line_id: null,
      amount: { value: null, currency: 'VND', status: 'unconfirmed', tax_basis: 'unknown' },
    } satisfies ContractLine;
    expect(lineDrafts([line], false)).toEqual([{ scopeKey: 'L1', name: 'Survey', amount: null, original: null, isNew: false }]);
    const [loaded] = lineDrafts([line], true);
    expect(loaded.amount).toEqual({ state: 'unconfirmed', value: '', taxBasis: 'unknown' });
    expect(lineInputs([loaded], true)).toEqual({ lines: [{ scope_key: 'L1', name: 'Survey' }] });
  });

  it('explains server errors and asks for a reload only when the data changed', () => {
    expect(workflowErrorMessage(error(409, 'stale_version', { current_version: 4 }))).toContain('Tải lại');
    expect(needsReload(error(409, 'stale_version'))).toBe(true);
    expect(needsReload(error(422, 'reason_required'))).toBe(false);
    expect(workflowErrorMessage(error(422, 'submission_incomplete', { problems: ['no_lines', 'tax_basis_mixed'] })))
      .toBe('Chưa gửi rà soát được: bản nháp chưa có dòng phạm vi; các dòng khác cơ sở thuế.');
    expect(workflowErrorMessage(error(400, 'invalid_request', { field: 'body.reason' }))).toBe('Dữ liệu gửi lên chưa hợp lệ. (body.reason)');
    expect(workflowErrorMessage(error(418, 'something_new'))).toBe('server something_new');
    expect(workflowErrorMessage(new TypeError('network'))).toContain('chưa được lưu');
  });
});
