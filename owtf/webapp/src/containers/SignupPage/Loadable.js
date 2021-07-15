/**
 * Asynchronously loads the component for SignupPage.
 */
import Loadable from "react-loadable";

import PageLoadingIndicator from "components/PageLoadingIndicator";

export default Loadable({
  loader: () => import("./index"),
  loading: PageLoadingIndicator
});
