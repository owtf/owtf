import React from 'react';
import {TARGET_UI_URI, TARGET_API_URI} from '../constants';
import Header from './Header';
import SideFilters from './SideFilters';

class Report extends React.Component {

    replaceContainer() {
        document.getElementById("app").parentElement.className = "container-fluid";
    };

    constructor(props) {
        super(props);

        this.state = {
            targetdata: {}
        }
    };

    /* Making an AJAX request on source property */
    componentDidMount() {
        var target_id = document.getElementById("report").getAttribute("data-code");
        this.serverRequest = $.get(TARGET_API_URI + target_id, function(result) {
            this.setState({targetdata: result});
        }.bind(this));
    };

    componentWillUnmount() {
        this.serverRequest.abort();
    };

    render() {
        this.replaceContainer.bind(this)();
        return (
            <div>
                <Header targetdata={this.state.targetdata}/>
                <div className="row">
                    <div className="col-sm-2 col-md-2 col-lg-2" id="plugin_nav">
                        <SideFilters/>
                    </div>
                    <div className="col-sm-10 col-md-10 col-lg-10">
                    </div>
                </div>
            </div>
        );
    }
}

export default Report;
