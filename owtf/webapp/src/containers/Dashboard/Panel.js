/*
 * Component to show if page not found.
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
