import { createSelector } from "reselect";

const selectMarketplace = (state: any) => state.get("marketplace");

export const makeSelectPlugins = createSelector(
  selectMarketplace,
  (s) => s.get("plugins").toJS()
);
export const makeSelectTotal = createSelector(selectMarketplace, (s) => s.get("total"));
export const makeSelectLoading = createSelector(selectMarketplace, (s) => s.get("loading"));
export const makeSelectError = createSelector(selectMarketplace, (s) => s.get("error"));
export const makeSelectFilter = createSelector(selectMarketplace, (s) => s.get("filter").toJS());
export const makeSelectUploadLoading = createSelector(
  selectMarketplace,
  (s) => s.get("uploadLoading")
);
export const makeSelectUploadError = createSelector(
  selectMarketplace,
  (s) => s.get("uploadError")
);
export const makeSelectUploadSuccess = createSelector(selectMarketplace, (s) => {
  const v = s.get("uploadSuccess");
  return v ? v.toJS() : null;
});
export const makeSelectRunLoading = createSelector(
  selectMarketplace,
  (s) => s.get("runLoading")
);
export const makeSelectRunError = createSelector(selectMarketplace, (s) => s.get("runError"));
export const makeSelectRunResult = createSelector(selectMarketplace, (s) => {
  const v = s.get("runResult");
  return v ? v.toJS() : null;
});
