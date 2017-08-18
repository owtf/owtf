import React from 'react';

/**
 * React Component for Home.
 *
 * - Renders on (URL)  - /ui/
 */

class Home extends React.Component {
    render() {
        return (
            <div>
                <ul className="breadcrumb">
                    <li className="active">Home</li>
                </ul>
                <div className="container-fluid jumbotron">
                    <h1>Offensive Web Testing Framework!</h1>
                    <p>
                        OWASP OWTF is a project that aims to make security assessments as efficient as possible. Some of the ways in which this is achieved are:
                    </p>
                    <ul>
                        <li>Separating the tests that require no permission from the ones that require permission (i.e. active/ bruteforce).</li>
                        <li>Launching a number of tools automatically.</li>
                        <li>Running tests not found in other tools.</li>
                        <li>Providing an interactive interface/report.</li>
                        <li>More info:
                            <a href="https://www.owasp.org/index.php/OWASP_OWTF" target="__blank__">https://www.owasp.org/index.php/OWASP_OWTF</a>
                        </li>
                    </ul>
                    <p>
                        <a className="btn btn-primary btn-lg" role="button" href="http://owtf.org" target="_blank">Learn more</a>
                    </p>
                </div>
            </div>
        );
    }
}

export default Home;
