import { useState } from "react";
import { useAPI } from "../lib/api";
import type { Profile } from "../lib/types";
import { Button, ErrorMessage, Loading, PageHead } from "../components/shared";

export default function Profiles() {
  const list = useAPI<Profile[]>("/profiles");
  const [name, setName] = useState("");
  const detail = useAPI<Profile>(
    name ? `/profiles/${encodeURIComponent(name)}` : "",
  );
  return (
    <>
      <PageHead
        title="Profiles"
        description="Plugin ordering for group launches. A profile does not restrict which plugins run."
      />
      <ErrorMessage error={list.error || detail.error} />
      {list.isPending ? (
        <Loading />
      ) : (
        <div className="stack">
          {list.data?.map((profile) => (
            <section className="panel" key={profile.name}>
              <div className="section-head">
                <h2>{profile.name}</h2>
                <Button variant="outline" onClick={() => setName(profile.name)}>
                  Show
                </Button>
              </div>
              <p>{profile.description}</p>
              {name === profile.name &&
                (detail.isPending ? (
                  <Loading />
                ) : (
                  detail.data && (
                    <ol>
                      {detail.data.plugins.map((id) => (
                        <li key={id}>
                          <code>{id}</code>
                        </li>
                      ))}
                    </ol>
                  )
                ))}
            </section>
          ))}
          {!list.data?.length && <p>No profiles configured.</p>}
        </div>
      )}
    </>
  );
}
