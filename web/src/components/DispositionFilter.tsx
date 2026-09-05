import { dispositions } from "../lib/types";

export default function DispositionFilter({
  values,
  onChange,
}: {
  values: string[];
  onChange: (values: string[]) => void;
}) {
  return (
    <fieldset className="filters">
      <legend>Output dispositions</legend>
      {dispositions.map((value) => (
        <label className="actions" key={value}>
          <input
            type="checkbox"
            checked={values.includes(value)}
            onChange={(event) =>
              onChange(
                event.target.checked
                  ? [...values, value]
                  : values.filter((item) => item !== value),
              )
            }
          />
          {value.replaceAll("_", " ")}
        </label>
      ))}
      <span className="muted">None selected includes all output.</span>
    </fieldset>
  );
}
