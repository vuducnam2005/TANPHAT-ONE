import type { Money } from '../../../shared/api/types';
import { formatMoney, taxBasisNote } from '../format';

export function MoneyValue({ money }: { money: Money | null | undefined }) {
  const note = taxBasisNote(money);
  return (
    <span className={`tp-money${money?.value == null ? ' is-missing' : ''}`}>
      {formatMoney(money)}
      {note && <small>{note}</small>}
    </span>
  );
}
