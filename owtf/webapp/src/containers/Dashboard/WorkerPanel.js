/*
 * Component to show if page not found.
 */
import React from "react";
import { Pane, Heading } from "evergreen-ui";
import { Pie } from 'react-chartjs-2';

export default class WorkerPanel extends React.Component {
  render() {
      // const chartData = {
      //   labels: this.props.chartData.map(severity => severity.label),
      //   datasets:[
      //     { 
      //       data: this.props.chartData.map(severity => severity.value),
      //       backgroundColor: this.props.chartData.map(severity => severity.color)
      //     }
      //   ]
      // }
    return (
      <Pane marginTop={20} paddingRight={20}>
        <Heading size={700}>Worker Panel</Heading>
        <hr />
        {/* <Pie
          data={chartData}
          width={300}
          height={100}
          options={{
            title:{
              display:false,
              text:"Current Vulnerabilities",
              fontSize:30
            },
            legend:{
              display:true,
              position:"right"
            },
            maintainAspectRatio: false
          }}
        /> */}
    </Pane>
    );
  }
}
