import { useState } from "react";
import { useAPI, params } from "../lib/api";
import type { Page } from "../lib/types";
import { ErrorMessage, Loading, Pager } from "./shared";
import { Input } from "./ui/input";

export default function DiscoveredURLs({ target }: { target: string }) {
  const [search, setSearch] = useState("");
  const [visited, setVisited] = useState("");
  const [scope, setScope] = useState("");
  const [offset, setOffset] = useState(0);
  const query = useAPI<Page<{ url: string; visited: boolean; scope: boolean }>>(
    `/targets/${target}/urls/search?${params({ search, offset, limit: 20, ...(visited ? { visited } : {}), ...(scope ? { scope } : {}) })}`,
  );
  return (
    <>
      <div className="filters">
        <label>
          Search URLs
          <Input
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setOffset(0);
            }}
          />
        </label>
        <label>
          Visited
          <select
            value={visited}
            onChange={(e) => {
              setVisited(e.target.value);
              setOffset(0);
            }}
          >
            <option value="">All</option>
            <option value="true">Yes</option>
            <option value="false">No</option>
          </select>
        </label>
        <label>
          URL scope
          <select
            value={scope}
            onChange={(e) => {
              setScope(e.target.value);
              setOffset(0);
            }}
          >
            <option value="">All</option>
            <option value="true">In scope</option>
            <option value="false">Out of scope</option>
          </select>
        </label>
      </div>
      <ErrorMessage error={query.error} />
      {query.isPending ? (
        <Loading />
      ) : (
        <>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>URL</th>
                  <th>Visited</th>
                  <th>Scope</th>
                </tr>
              </thead>
              <tbody>
                {query.data?.data.map((url) => (
                  <tr key={url.url}>
                    <td>{url.url}</td>
                    <td>{url.visited ? "Yes" : "No"}</td>
                    <td>{url.scope ? "In scope" : "Out of scope"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pager
            offset={offset}
            total={query.data?.records_filtered || 0}
            onChange={setOffset}
          />
        </>
      )}
    </>
  );
}
