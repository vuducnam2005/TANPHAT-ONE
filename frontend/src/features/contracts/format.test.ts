import { describe, expect, it } from 'vitest';
import { formatDate, formatDecimal, formatMoney, taxBasisNote } from './format';
import { parseRouteId } from './queries';

const money = (value: string | null, status: 'confirmed' | 'unconfirmed' | 'incomplete' | 'empty' | 'mixed_basis' = 'confirmed') =>
  ({ value, currency: 'VND', status, tax_basis: 'excluding_tax' as const });

describe('contract money display', () => {
  it('groups decimal strings without converting them to floating point', () => {
    expect(formatDecimal('110000000')).toBe('110.000.000');
    expect(formatDecimal('-1234.50')).toBe('-1.234,50');
    expect(formatDecimal('0')).toBe('0');
    // Beyond Number.MAX_SAFE_INTEGER every digit is still preserved.
    expect(formatDecimal('90071992547409931')).toBe('90.071.992.547.409.931');
    expect(formatDecimal('1e9')).toBeNull();
  });

  it('keeps zero, missing and unconfirmed values distinct', () => {
    expect(formatMoney(money('0'))).toBe('0 VND');
    expect(formatMoney(money(null, 'unconfirmed'))).toBe('Chưa xác nhận');
    expect(formatMoney(money(null, 'incomplete'))).toBe('Chưa đủ: có dòng chưa xác nhận');
    expect(formatMoney(money(null, 'mixed_basis'))).toBe('Không cộng được: khác cơ sở thuế');
    expect(formatMoney(null)).toBe('Chưa có dữ liệu giá trị');
    expect(formatMoney(money('not-a-number'))).toBe('Giá trị không hợp lệ');
    expect(taxBasisNote(money('100'))).toBe('chưa gồm thuế');
    expect(taxBasisNote(money(null, 'unconfirmed'))).toBeNull();
  });

  it('renders dates without timezone shifts and rejects unsafe route ids', () => {
    expect(formatDate('2026-11-01')).toBe('01/11/2026');
    expect(formatDate(null)).toBe('Chưa ghi nhận');
    expect(parseRouteId('42')).toBe(42);
    for (const value of ['0', '-1', '1.5', 'abc', '99999999999999999999', undefined, null]) {
      expect(parseRouteId(value)).toBeUndefined();
    }
  });
});
