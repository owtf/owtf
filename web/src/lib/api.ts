import {
  QueryClient,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";

// Reads can be refreshed explicitly. Never replay a launch after a lost response.
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: false,
      staleTime: 2000,
      refetchOnWindowFocus: false,
      refetchIntervalInBackground: false,
    },
    mutations: { retry: false },
  },
});
export async function request<T>(
  path: string,
  method = "GET",
  body?: unknown,
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(`/api/v2${path}`, {
    method,
    signal,
    headers:
      body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const result = await response.json().catch(() => null);
    throw new Error(result?.error || `Request failed (${response.status})`);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}
export function useAPI<T>(
  path: string,
  poll: boolean | ((data: T | undefined) => boolean) = false,
) {
  return useQuery<T>({
    queryKey: ["api", path],
    queryFn: ({ signal }) => request<T>(path, "GET", undefined, signal),
    enabled: !!path,
    refetchInterval: (query) =>
      (typeof poll === "function" ? poll(query.state.data) : poll)
        ? 2000
        : false,
  });
}
export function useAction<T = unknown>(action: (input: T) => Promise<unknown>) {
  const client = useQueryClient();
  return useMutation({
    mutationFn: action,
    onSettled: () => client.invalidateQueries({ queryKey: ["api"] }),
  });
}
export const params = (values: Record<string, string | number>) =>
  new URLSearchParams(
    Object.entries(values).map(([k, v]) => [k, String(v)]),
  ).toString();
