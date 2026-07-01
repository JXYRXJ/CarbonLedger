import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { walletApi } from "@/services/walletApi.js";

export const useWallet = () =>
  useQuery({ queryKey: ["wallet"], queryFn: () => walletApi.get() });

export const useWalletTransactions = (params) =>
  useQuery({ queryKey: ["wallet-transactions", params], queryFn: () => walletApi.transactions(params) });

export const useConnectWallet = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: walletApi.connect,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["wallet"] }),
  });
};

export const useDisconnectWallet = () => {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: walletApi.disconnect,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["wallet"] }),
  });
};