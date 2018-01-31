import React from 'react';
import { push } from 'react-router-redux';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';


class HomeView extends React.Component {
    static propTypes = {
        dispatch: PropTypes.func.isRequired
    };

    static defaultProps = {
    };

    render() {
        return (
            <div className="container">
                <div className="text-center">
                    <h1>Django React Redux Demo</h1>
                    <h4>Hello, guest</h4>
                </div>
            </div>
        );
    }
}

const mapStateToProps = (state) => {
    return {
    };
};

export default connect(mapStateToProps)(HomeView);
export { HomeView as HomeViewNotConnected };
