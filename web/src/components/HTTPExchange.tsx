import { useQuery } from "@tanstack/react-query";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "./ui/tabs";
import { ErrorMessage, Loading } from "./shared";

type Message = {
  line: string;
  headers: string | Record<string, string[]>;
  body?: string;
  artifact?: string;
};

function headersText(headers: Message["headers"]) {
  try {
    const values = typeof headers === "string" ? JSON.parse(headers) : headers;
    return Object.entries(values)
      .flatMap(([key, value]) =>
        (Array.isArray(value) ? value : [value]).map(
          (item) => `${key}: ${item}`,
        ),
      )
      .join("\n");
  } catch {
    return String(headers);
  }
}

function Body({ message }: { message: Message }) {
  const query = useQuery({
    queryKey: ["http-body", message.artifact],
    enabled: !!message.artifact,
    retry: false,
    queryFn: async ({ signal }) => {
      const response = await fetch(`/api/v2/artifacts/${message.artifact}`, {
        signal,
      });
      if (!response.ok)
        throw new Error(`Body unavailable (${response.status})`);
      const reader = response.body?.getReader();
      if (!reader) return "";
      const decoder = new TextDecoder();
      let text = "",
        size = 0;
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const remaining = (1 << 20) - size;
          text += decoder.decode(value.subarray(0, remaining), {
            stream: true,
          });
          size += value.length;
          if (size > 1 << 20)
            return (
              text + "\n[Preview limited to 1 MiB; download for full body]"
            );
        }
        return text + decoder.decode();
      } finally {
        await reader.cancel();
      }
    },
  });
  let content = query.data;
  if (!message.artifact && message.body) {
    try {
      content = new TextDecoder().decode(
        Uint8Array.from(atob(message.body), (c) => c.charCodeAt(0)),
      );
    } catch {
      content = "Invalid base64 body";
    }
  }
  return (
    <>
      {message.artifact && (
        <a
          href={`/api/v2/artifacts/${message.artifact}`}
          target="_blank"
          rel="noreferrer"
        >
          Download body
        </a>
      )}
      <ErrorMessage error={query.error} />
      {message.artifact && query.isPending ? (
        <Loading />
      ) : (
        <pre>{content || "Empty body"}</pre>
      )}
    </>
  );
}

// Captured content is always rendered as text, never as executable HTML.
export default function HTTPExchange({
  request,
  response,
}: {
  request: Message;
  response: Message;
}) {
  return (
    <Tabs defaultValue="request">
      <TabsList aria-label="HTTP message">
        <TabsTrigger value="request">Request</TabsTrigger>
        <TabsTrigger value="response">Response</TabsTrigger>
      </TabsList>
      {Object.entries({ request, response }).map(([side, message]) => (
        <TabsContent key={side} value={side}>
          <pre>{message.line}</pre>
          <Tabs defaultValue="headers">
            <TabsList aria-label={`${side} content`}>
              <TabsTrigger value="headers">Headers</TabsTrigger>
              <TabsTrigger value="body">Body</TabsTrigger>
            </TabsList>
            <TabsContent value="headers">
              <pre>{headersText(message.headers) || "No headers"}</pre>
            </TabsContent>
            <TabsContent value="body">
              <Body message={message} />
            </TabsContent>
          </Tabs>
        </TabsContent>
      ))}
    </Tabs>
  );
}
