/**
 * Asynchronously loads the component for Report.
 */
import Loadable from "react-loadable";

import PageLoadingIndicator from "../../components/PageLoadingIndicator";

export default Loadable({
  loader: () => import("./index"),
  loading: PageLoadingIndicator
});
