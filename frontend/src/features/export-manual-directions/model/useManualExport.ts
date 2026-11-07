import { useMutation } from '@tanstack/react-query';
import { manualDirectionApi } from '@/entities/manual-direction';
import { downloadJson } from '@/shared/lib/download';

export function useManualExport() {
  return useMutation({
    mutationFn: manualDirectionApi.exportData,
    onSuccess: (data) => downloadJson(data, `admitflow-${data.exportedAt.slice(0, 10)}.json`),
  });
}
