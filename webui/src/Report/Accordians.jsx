import React from 'react';
import Accordian from './Accordian.jsx';
import {TARGET_API_URI, STATIC_URI} from '../constants.jsx';

/**
  * React Component for group of Accordian. It is child component used by Report Component.
  * Uses REST API - /api/targets/<target_id>/poutput/names/
  * JSON output will contain a JS object having key as Plugin Code and value is another JS object having data and details keys.
  * data gives all details about that plugin result other than output.
  * details gives information of plugin like desciption, url etc.
  * Idea behind using the /api/targets/<target_id>/poutput/names/ thing to load only the things that are visible to user.
  * Output is not visible to user which can be a huge data to request initially. Hence, this optimises the Report a lot.
  */

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
        }.bind(this))
        .fail(function() {
            this.setState({isLoaded: true});
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
