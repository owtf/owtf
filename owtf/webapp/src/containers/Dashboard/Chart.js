/**
 *  React Component for Pie Chart.
 *  It is child components which is used by Dashboard.js
 *  Uses npm package - react-chartjs2 (https://github.com/reactjs/react-chartjs) to create Pie chart
 *  Uses Rest API - /api/targets/severitychart/ (Obtained from props)
 * JSON response object:
 * {
 *  "data": [
 *    {
 *      "color": "#A9A9A9",
 *      "id": 0,
 *      "value": <int>,
 *      "label": "Not Ranked"
 *    },
 *    {
 *      "color": "#b1d9f4",
 *      "id": 2,
 *      "value": <int>,
 *      "label": "Info"
 *    },
 *    {
 *      "color": "#337ab7",
 *      "id": 3,
 *      "value": <int>,
 *      "label": "Low"
 *    },
 *    {
 *      "color": "#c12e2a",
 *      "id": 5,
 *      "value": <int>,
 *      "label": "High"
 *    },
 *    {
 *      "color": "#800080",
 *      "id": 6,
 *      "value": <int>,
 *      "label": "Critical"
 *    }
 *  ]
 *}
 *  Each element of data array represent details of one severity. Value is number of targets belongs to that severity.
 */

import React from "react";
import { Pie } from 'react-chartjs-2';

export default class Chart extends React.Component {
  render() {
      const chartData = {
        labels: this.props.chartData.map(severity => severity.label),
        datasets:[
          { 
            data: this.props.chartData.map(severity => severity.value),
            backgroundColor: this.props.chartData.map(severity => severity.color)
          }
        ]
      }
    return (
      <Pie
        data={chartData}
        width={100}
        height={100}
        options={{
          title:{
            display:false
          },
          legend:{
            display:true,
            position:"left"
          },
          maintainAspectRatio: false
        }}
      />
    );
  }
}
