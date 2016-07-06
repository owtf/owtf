import React from 'react';

class Transactions extends React.Component {

    /* Function which replace the container to full width */
    replaceContainer() {
        document.getElementById("app").parentElement.className = "container-fluid";
    };

    render() {
        this.replaceContainer.bind(this)();
        return (
            <div></div>
        );
    }
}

export default Transactions;
