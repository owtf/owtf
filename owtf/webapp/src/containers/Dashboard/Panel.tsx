/**
 * React Component for VulnerabilityPanel.
 * It is child components which is used by Dashboard.js
 * Uses REST API  - /api/dashboard/severitypanel/
 * JSON output format -
 * {
 *    "data":[
 *       {
 *          "id":5,
 *          "value":<int>,
 *          "label":"Critical"
 *       },
 *       {
 *          "id":4,
 *          "value":<int>,
 *          "label":"High"
 *       },
 *       {
 *          "id":3,
 *          "value":<int>,
 *          "label":"Medium"
 *       },
 *       {
 *          "id":2,
 *          "value":<int>,
 *          "label":"Low"
 *       },
 *       {
 *          "id":1,
 *          "value":<int>,
 *          "label":"Info"
 *       },
 *       {
 *          "id":0,
 *          "value":<int>,
 *          "label":"Passing"
 *       }
 *     ]
 * }
 *  Each element of data array represent one block of VulnerabilityPanel representing one severity count
 */

import React from "react";
import { Bar } from "react-chartjs-2";


interface propsType {
  panelData: []
}
export default class VulnerabilityPanel extends React.Component <propsType>{
  render() {
    const chartData = {
      labels: this.props.panelData.map((severity:any) => severity.label),
      datasets: [
        {
          label: "Severity",
          data: this.props.panelData.map((severity:any) => severity.value),
          backgroundColor: [
            "#c275f5",
            "#ff7a7a",
            "#f2f67e",
            "#a3d3ff",
            "#53b0ee",
            "#85D262 "
          ]
        }
      ]
    };
    return (
      <Bar
        data={chartData}
        height={270}
        options={{
          title: {
            display: false,
            text: "Current Vulnerabilities",
            fontSize: 40
          },
          legend: {
            display: false,
            position: "right"
          },
          maintainAspectRatio: false
        }}
      />
    );
  }
}
