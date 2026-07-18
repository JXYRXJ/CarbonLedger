import api from "./axios.js";

export const portfolioApi = {
  get: (params) => api.get("/portfolio", { params }).then((r) => {
    const batches = r.data?.owned_batches || r.data?.ownedBatches || [];
    return batches.map((h) => {
      const ownedCredits = h.total_credits_owned ?? h.ownedCredits ?? 0;
      const availableCredits = h.available_credits ?? h.availableCredits ?? 0;
      const avgPrice = h.average_purchase_price ?? h.averagePurchasePrice ?? 0;
      const currentValue = ownedCredits * avgPrice;
      const id = h.ownership_id || h.ownershipId || h.id;
      
      return {
        ...h,
        id,
        ownedCredits,
        availableCredits,
        currentValue,
        batchNumber: h.batch_number || h.batchNumber || h.batch?.batchNumber,
        projectName: h.project?.name || h.projectName || h.batch?.project?.name,
        batchId: h.batch_id || h.batchId,
        batch: {
          id: h.batch_id || h.batchId || h.batch?.id,
          batchNumber: h.batch_number || h.batchNumber || h.batch?.batchNumber,
          project: h.project || h.batch?.project,
        }
      };
    });
  }),
  summary: () => api.get("/portfolio/summary").then((r) => r.data),
};