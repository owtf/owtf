import React from 'react';
import { reduxForm, Field } from 'redux-form';

import '../index.scss';
import { Col } from 'react-flexbox-grid';


const AddTargets = ({ invalid, submitting, reset }) => {
  const handleSubmit = (values) => {
    console.log(values);
  };

  return (
    <form onSubmit={handleSubmit}>
        <h2>Add targets</h2>
        <div>
          <Field
            name="targets"
            component="textarea"
            type="text"
            placeholder="Targets separated by newline"
          />
        </div><br/>
        <div>
          <button className="btn btn-primary" type="submit" disabled={invalid || submitting}>Add</button>
        </div>
    </form>
  );
};
export default reduxForm({ form: 'addTargets' })(AddTargets);