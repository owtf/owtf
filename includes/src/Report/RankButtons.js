import React from 'react';

class RankButtons extends React.Component {

    render() {
        var obj = this.props.obj;
        var user_rank = obj['user_rank'];
        var owtf_rank = obj['owtf_rank'];
        if (user_rank in [0,
            1,
            2,
            3,
            4,
            5]) {
            return (
                <div className="btn-group">
                    <button type="button" className={user_rank === 0
                        ? "btn active"
                        : "btn"}>
                        <i className="fa fa-thumbs-up"></i>
                    </button>
                    <button type="button" className={user_rank === 1
                        ? "btn active btn-success"
                        : "btn"}>
                        <i className="fa fa-info-circle"></i>
                    </button>
                    <button type="button" className={user_rank === 2
                        ? "btn active btn-info"
                        : "btn"}>
                        <i className="fa fa-exclamation-circle"></i>
                    </button>
                    <button type="button" className={user_rank === 3
                        ? "btn active btn-warning"
                        : "btn"}>
                        <i className="fa fa-thumbs-up"></i>
                    </button>
                    <button type="button" className={user_rank === 4
                        ? "btn active btn-danger"
                        : "btn"}>
                        <i className="fa fa-bell"></i>
                    </button>
                    <button type="button" className={user_rank === 5
                        ? "btn active btn-critical"
                        : "btn"}>
                        <i className="fa fa-bomb"></i>
                    </button>
                </div>
            );
        } else {
            return (
                <div className="btn-group">
                    <button type="button" className={user_rank === 0
                        ? "btn active"
                        : "btn"}>
                        <i className="fa fa-thumbs-up"></i>
                    </button>
                    <button type="button" className={owtf_rank === 1
                        ? "btn active btn-success"
                        : "btn"}>
                        <i className="fa fa-info-circle"></i>
                    </button>
                    <button type="button" className={owtf_rank === 2
                        ? "btn active btn-info"
                        : "btn"}>
                        <i className="fa fa-exclamation-circle"></i>
                    </button>
                    <button type="button" className={owtf_rank === 3
                        ? "btn active btn-warning"
                        : "btn"}>
                        <i className="fa fa-thumbs-up"></i>
                    </button>
                    <button type="button" className={owtf_rank === 4
                        ? "btn active btn-danger"
                        : "btn"}>
                        <i className="fa fa-bell"></i>
                    </button>
                    <button type="button" className={user_rank === 5
                        ? "btn active btn-critical"
                        : "btn"}>
                        <i className="fa fa-bomb"></i>
                    </button>
                </div>
            );
        }
    }
}

export default RankButtons;
