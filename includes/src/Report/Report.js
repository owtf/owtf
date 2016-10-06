import React from 'react';
import {TARGET_UI_URI, TARGET_API_URI} from '../constants';
import Header from './Header';
import SideFilters from './SideFilters';
import Accordians from './Accordians';

class Report extends React.Component {

    replaceContainer() {
        document.getElementById("app").parentElement.className = "container-fluid";
    };

    constructor(props) {
        super(props);

        this.state = {
            targetdata: {},
            pluginNameData: {},
            pluginData: {}
        }
        this.pluginDataUpdate = this.pluginDataUpdate.bind(this);
    };

    pluginDataUpdate(key) {
        var target_id = document.getElementById("report").getAttribute("data-code");
        var presentState = this.state.pluginData;
        $.get(TARGET_API_URI + target_id + '/poutput/?plugin_code=' + key, function(result) {
            presentState[key] = result;
            this.setState({pluginData: presentState});
        }.bind(this));
    };

    /* Making an AJAX request on source property */
    componentDidMount() {
        var target_id = document.getElementById("report").getAttribute("data-code");
        var pluginDataUpdate = this.pluginDataUpdate;
        this.serverRequest1 = $.get(TARGET_API_URI + target_id, function(result) {
            this.setState({targetdata: result});
        }.bind(this));

        this.serverRequest2 = $.get(TARGET_API_URI + target_id + '/poutput/names/', function(result) {
            this.setState({pluginNameData: result});
            Object.keys(result).forEach(function(key,index) {
                pluginDataUpdate(key);
            });
        }.bind(this));
    };

    componentWillUnmount() {
        this.serverRequest1.abort();
        this.serverRequest2.abort();
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
                        <Accordians plugins={this.state.pluginNameData} pluginData={this.state.pluginData} />
                    </div>
                </div>
            </div>
        );
    }
}

export default Report;
