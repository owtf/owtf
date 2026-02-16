/**
 * Asynchronously loads the route component.
 */
import React, { Suspense, lazy } from "react";

import PageLoadingIndicator from "../../components/PageLoadingIndicator";

const LazyComponent = lazy(() => import("./index"));

export default function LoadableComponent(props: any) {
  return React.createElement(
    Suspense,
    { fallback: React.createElement(PageLoadingIndicator) },
    React.createElement(LazyComponent as React.ComponentType<any>, props),
  );
}
