import React from 'react';
import Accordian from './Accordian';
import {TARGET_API_URI, STATIC_URI} from '../constants';

class Accordians extends React.Component {

    constructor(props) {
        super(props);

        this.state = {
            pluginNameData: {},
            isLoaded: false
        };
    };

    /* Making an AJAX request on source property */
    componentDidMount() {
        var target_id = document.getElementById("report").getAttribute("data-code");
        this.serverRequest = $.get(TARGET_API_URI + target_id + '/poutput/names/', function(result) {
            this.setState({pluginNameData: result, isLoaded: true});
        }.bind(this));
    };

    componentWillUnmount() {
        this.serverRequest.abort();
    };

    render() {
        var plugins = this.state.pluginNameData;
        if (this.state.isLoaded) {
            return (
                <div className="panel-group" id="pluginOutputs">
                    {Object.keys(plugins).map(function(key) {
                        return (<Accordian data={plugins[key]} code={key}/>);
                    })}
                </div>
            );
        } else {
            return (
                <div>
                    <img src={STATIC_URI + "img/Preloader_big.gif"} alt="Loader" style={{"display": "block", "margin": "auto"}}/>
                </div>
            );
        }
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
