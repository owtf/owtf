/*
 * Component to show if page not found.
 */
import React from "react";

export default class NotFoundPage extends React.Component {
  render() {
    return (
      <p
        style={{
          textAlign: "center",
          fontSize: "40px",
          margin: "150px auto",
          fontWeight: "bold"
        }}
      >
        Page Not Found
      </p>
    );
  }
}
