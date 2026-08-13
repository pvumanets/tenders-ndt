export type Me = {
  username: string;
  display_name: string;
};

export async function fetchMe(): Promise<Me | null> {
  try {
    const res = await fetch("/api/me", { credentials: "include" });
    if (!res.ok) return null;
    return (await res.json()) as Me;
  } catch {
    return null;
  }
}

export async function login(username: string, password: string): Promise<boolean> {
  const res = await fetch("/api/auth/login", {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  return res.ok;
}

export async function logout(): Promise<void> {
  await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
}
