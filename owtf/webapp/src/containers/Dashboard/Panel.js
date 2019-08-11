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
import { Bar } from 'react-chartjs-2';

export default class VulnerabilityPanel extends React.Component {
  render() {
      const chartData = {
        labels: this.props.panelData.map(severity => severity.label),
        datasets:[
          { 
            label:'Severity',
            data: this.props.panelData.map(severity => severity.value),
            backgroundColor:[
              '#800080',
              '#c12e2a',
              '#fc0',
              '#337ab7',
              '#b1d9f4',
              '#32cd32',
            ]
          }
        ]
      }
    return (
      <Bar
        data={chartData}
        height={150}
        options={{
          title:{
            display:false,
            text:"Current Vulnerabilities",
            fontSize:30
          },
          legend:{
            display:false,
            position:"right"
          },
          maintainAspectRatio: false
        }}
      />
    );
  }
}
