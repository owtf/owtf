/*
 * Component to show if page not found.
 */
import React from "react";
import { Pane, Heading } from "evergreen-ui";
import {Bar, Line, Pie, Doughnut, Bubble} from 'react-chartjs-2';

export default class VulnerabilityPanel extends React.Component {
  render() {
      const chartData = {
        labels: this.props.panelData.map(severity => severity.label),
        datasets:[
          { 
            label:'Severity',
            data: this.props.panelData.map(severity => severity.value),
            // data: [1,1,1,2,1,2],
            backgroundColor:[
              '#732673',
              '#ac2925',
              '#d58512',
              '#337ab7',
              '#269abc',
              '#398439',
            ]
          }
        ]
      }
    return (
      <Pane marginTop={20} padding={20}>
        <Heading size={700}>Current Vulnerabilities</Heading>
        <hr />
        <Bar
          data={chartData}
          width={100}
          height={400}
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
    </Pane>
    );
  }
}
