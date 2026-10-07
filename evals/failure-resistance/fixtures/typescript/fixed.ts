export type Account = { id: string };
export function decode(raw: unknown): Account {
  if (!raw || typeof raw !== "object" || typeof (raw as {id?: unknown}).id !== "string") throw new TypeError("invalid account");
  return {id: (raw as {id: string}).id};
}
