export async function generateAdjusterBrief(claimJson) {
  const response = await fetch(
    "https://ai-claims-orchestrator.onrender.com/generate-adjuster-brief",
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ claim_json: claimJson }),
    }
  );

  if (!response.ok) {
    throw new Error("Failed to generate adjuster brief");
  }

  return await response.json();
}
