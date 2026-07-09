const API_BASE = "http://127.0.0.1:8000";

export async function analyzeBridge(data: any) {
  const response = await fetch(
    `${API_BASE}/bridge/analyze`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    }
  );

  return response.json();
}