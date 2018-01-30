import React, { Component } from 'react';
import { connect } from 'react-redux';
import { push } from 'react-router-redux';
import classNames from 'classnames';
import PropTypes from 'prop-types';


class App extends Component {
    static propTypes = {
        children: PropTypes.shape().isRequired,
        dispatch: PropTypes.func.isRequired,
        location: PropTypes.shape({
            pathname: PropTypes.string
        })
    };

    static defaultProps = {
        location: undefined
    };

    goToIndex = () => {
        this.props.dispatch(push('/'));
    };

    render() {
        const homeClass = classNames({
            active: this.props.location && this.props.location.pathname === '/'
        });

        return (
            <div className = "app" > 
                <nav className="navbar navbar-default">
                    <div className="container-fluid">
                        <div className="navbar-header">
                            <button
                                type="button"
                                className="navbar-toggle collapsed"
                                data-toggle="collapse"
                                data-target="#top-navbar"
                                aria-expanded="false">
                                <span className="sr-only">Toggle navigation</span>
                                <span className="icon-bar"/>
                                <span className="icon-bar"/>
                                <span className="icon-bar"/>
                            </button>
                            <a className="navbar-brand" onClick={this.goToIndex}>
                                Django React Redux Demo
                            </a>
                        </div>
                    </div>
                </nav> 
            </div>
        );
    }
}

const mapStateToProps = (state, ownProps) => {
    return {
        location: state.routing.location
    };
};

export default connect(mapStateToProps)(App);
export { App as AppNotConnected };
