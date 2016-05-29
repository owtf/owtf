import React from 'react';
import Chart from './Chart'
import { SEVERITY_CHART_URL } from '../constants'

class Home extends React.Component {
   render() {
      return (
        <div className="container-fluid">
          <div className="row">
            <div className="col-xs-12 col-md-6 nopadding">
              <h1>Welcome to OWTF</h1>
            </div>
          </div>
          <div className="row">
            <div className="col-xs-12 col-md-6">
              <h3>Previous Targets Analytics</h3><br/>
            </div>
          </div>
          <div className="row">
            <Chart source={SEVERITY_CHART_URL}/>
          </div>
        </div>
      );
   }
}

export default Home;