import React from 'react';
import {TARGET_UI_URI} from '../constants';

class Header extends React.Component {

    render() {
        return (
            <div>
                <ul className="breadcrumb">
                    <li>
                        <a href="/">Home</a>
                    </li>
                    <li>
                        <a href={TARGET_UI_URI}>Target</a>
                    </li>
                    <li className="active">{this.props.targetdata.target_url}</li>
                </ul>

                {/* Scroll to top */}
                <a href="javascript:" id="return-to-top">
                    <i className="fa fa-chevron-up"></i>
                </a>
                {/* End of scroll to top */}

                <div className="col-md-10 col-md-offset-2">
                    <div className="page-header">
                        <div className="row">
                            <div className="col-md-8">
                                <h2 style={{
                                    wordWrap: "break-word"
                                }}>
                                    {this.props.targetdata.target_url}
                                    <small>
                                        {' (' + this.props.targetdata.host_ip + ')'}
                                    </small>
                                </h2>
                            </div>
                            <div className="col-md-4">
                                <h3 id="rankingTargetInfo"></h3>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        );
    }
}

export default Header;
