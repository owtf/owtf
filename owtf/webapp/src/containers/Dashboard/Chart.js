/*
 * Component to show if page not found.
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
