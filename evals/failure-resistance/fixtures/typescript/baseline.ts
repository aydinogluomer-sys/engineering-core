export type Account = { id: string };
export function decode(raw: unknown): Account { return raw as Account; }
