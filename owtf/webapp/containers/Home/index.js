import React, { Component } from 'react';
import { push } from 'react-router-redux';
import { connect } from 'react-redux';
import PropTypes from 'prop-types';


class HomeView extends Component {
    static propTypes = {
        dispatch: PropTypes.func.isRequired
    };

    render() {
        return (
            <div>"hi"
            </div>
        );
    }
}

export { HomeView as HomeViewNotConnected };
