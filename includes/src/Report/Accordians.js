import React from 'react';
import Accordian from './Accordian';
import {TARGET_API_URI} from '../constants';

class Accordians extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            pluginNameData: {}
        };
    };

    /* Making an AJAX request on source property */
    componentDidMount() {
        var target_id = document.getElementById("report").getAttribute("data-code");
        this.serverRequest = $.get(TARGET_API_URI + target_id + '/poutput/names/', function(result) {
            this.setState({pluginNameData: result});
        }.bind(this));
    };

    componentWillUnmount() {
        this.serverRequest.abort();
    };

    render() {
        var plugins = this.state.pluginNameData;
        return (
            <div className="panel-group" id="pluginOutputs">
                {Object.keys(plugins).map(function(key) {
                    return (<Accordian data={plugins[key]} code={key}/>);
                })}
            </div>
        );
    }
}

Accordians.contextTypes = {
    selectedType: React.PropTypes.array,
    selectedRank: React.PropTypes.array,
    selectedGroup: React.PropTypes.array,
    selectedOwtfRank: React.PropTypes.array,
    selectedStatus: React.PropTypes.array,
    selectedMapping: React.PropTypes.string
};

export default Accordians;
