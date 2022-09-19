/*
 * SignupPage.
 * Handles the signup of the new user
 * Redirects to the email verification page after input validation
 */

import React, {useState} from "react";
import {
  Pane,
  Heading,
  Button,
  Paragraph,
  Link,
  TextInputField,
  toaster,
  Icon,
  Text
} from "evergreen-ui";
import { signupStart } from "./actions";
import { connect } from "react-redux";
import PropTypes from "prop-types";

interface ISignupPage{
  onSignup: Function;
}

export function SignupPage({
    onSignup
  }: ISignupPage) {
  
  const [username, setUsername] = useState(""); //username of the user to be added
  const [email, setEmail] = useState(""); //email of the user to be added
  const [password, setPassword] = useState(""); //password of the user to be added
  const [confirmPassword, setConfirmPassword] = useState(""); //confirmPassword of the user to be added
  const [errors, setErrors] = useState({}); //stores errors during form validation
  const [hidePassword, setHidePassword] = useState(true); //handles visibility of password input field
  const [hideConfirmPassword, setHideConfirmPassword] = useState(true); //handles visibility of confirmPassword input field
  
  /**
   * Function handles the input validation for all the text input elements
   * @param {object} e event which triggered this function
   */
  const handleValidation = (e: { target: { name: string; }; }) => {
    let formIsValid = true;
    let errorss: {username: string, email: string, password: string, confirmPassword: string} = {};

    //Username
    if (e.target.name === "text-input-name" && !username) {
      formIsValid = false;
      errorss["username"] = "Username can't be empty";
    }

    //Email
    else if (e.target.name === "text-input-email" && !email) {
      formIsValid = false;
      errorss["email"] = "Email can't be empty";
    } else if (
      e.target.name === "text-input-email" &&
      typeof email !== "undefined"
    ) {
      if (
        !email.match(
          /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$/
        )
      ) {
        formIsValid = false;
        errorss["email"] = "Please enter a valid email";
      }
    }

    // Password
    if (e.target.name === "text-input-password" && !password) {
      formIsValid = false;
      errorss["password"] = "Password can't be empty";
    } else if (
      e.target.name === "text-input-password" &&
      typeof password !== "undefined"
    ) {
      if (
        !password.match(
          /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[^a-zA-Z0-9])(?!.*\s).{8,15}$/
        )
      ) {
        formIsValid = false;
        errorss["password"] = "Must have capital, small, number & special chars";
      }
    }

    // Confirm Password
    if (
      e.target.name === "text-input-confirm-password" &&
      !confirmPassword
    ) {
      formIsValid = false;
      errorss["confirmPassword"] = "Confirm Password can't be empty";
    } else if (
      e.target.name === "text-input-confirm-password" &&
      password !== confirmPassword
    ) {
      formIsValid = false;
      errorss["confirmPassword"] = "Password doesn't match";
    }

    setErrors(errors);
    return formIsValid;
  };

  /**
   * Function handles the signup of the user
   */
  const onSignupHandler = () => {
    onSignup(
      email,
      password,
      confirmPassword,
      username
    );
  };

  return (
    <Pane marginY={60} data-test="signupPageComponent">
      <Pane
        justifyContent="center"
        width="35%"
        elevation={1}
        margin="auto"
        padding={5}
      >
        <Heading
          size={700}
          textAlign="center"
          marginBottom={20}
          paddingTop={20}
        >
          Signup
        </Heading>
        <TextInputField
          label="Your OWTF Username"
          placeholder="Username"
          width="60%"
          marginLeft="20%"
          marginBottom={10}
          name="text-input-name"
          value={username}
          onChange={e => setUsername(e.target.value)}
          onBlur={e => handleValidation(e)}
          validationMessage={errors["username"]}
        />
        <TextInputField
          label="Email Address"
          placeholder="Email"
          width="60%"
          marginLeft="20%"
          marginBottom={10}
          name="text-input-email"
          value={email}
          onChange={e => setEmail(e.target.value)}
          onBlur={e => handleValidation(e)}
          validationMessage={errors["email"]}
        />
        <Pane position="relative">
          <Pane width="10%" marginLeft="75%" position="absolute">
            <Icon
              icon={hidePassword ? "eye-off" : "eye-open"}
              cursor="pointer"
              marginX={-10}
              marginY={32}
              onMouseDown={e => setHidePassword(false)}
              onMouseUp={e => setHidePassword(true)}
            />
          </Pane>
          <TextInputField
            label="Choose a Password"
            hint="Must have capital, small, number & special chars"
            placeholder="Password"
            width="60%"
            marginLeft="20%"
            name="text-input-password"
            value={password}
            type={hidePassword ? "password" : "text"}
            onChange={e => setPassword(e.target.value)}
            onBlur={e => handleValidation(e)}
            validationMessage={errors["password"]}
            marginBottom={5}
          />
        </Pane>
        <Pane position="relative" paddingTop={0} marginTop={0}>
          <Pane width="10%" marginLeft="75%" position="absolute">
            <Icon
              icon={hideConfirmPassword ? "eye-off" : "eye-open"}
              cursor="pointer"
              marginX={-10}
              marginY={32}
              onMouseDown={e => setHideConfirmPassword(false)}
              onMouseUp={e => setHideConfirmPassword(true)}
            />
          </Pane>
          <TextInputField
            label="Confirm Password"
            placeholder="Confirm Password"
            width="60%"
            marginLeft="20%"
            name="text-input-confirm-password"
            value={confirmPassword}
            type={hideConfirmPassword ? "password" : "text"}
            onChange={e => setConfirmPassword(e.target.value)}
            onBlur={e => handleValidation(e)}
            validationMessage={errors["confirmPassword"]}
          />
        </Pane>
        <Button
          width="20%"
          marginLeft="40%"
          justifyContent="center"
          appearance="primary"
          intent="none"
          onClick={onSignupHandler}
          disabled={
            Object.keys(errors).length === 0 &&
            errors.constructor === Object
              ? false
              : true
          }
        >
          SIGNUP
        </Button>
        <Paragraph
          size={300}
          width="60%"
          marginLeft="20%"
          marginTop={10}
          marginBottom={10}
        >
          Already have an account? <Link href="/login">Login</Link>
        </Paragraph>
      </Pane>
    </Pane>
  );
}

SignupPage.propTypes = {
  onSignup: PropTypes.func
};

const mapDispatchToProps = (dispatch: Function) => {
  return {
    onSignup: (email: string, password: string, confirmPassword: string, name: string) =>
      dispatch(signupStart(email, password, confirmPassword, name))
  };
};

export default connect(
  null,
  mapDispatchToProps
)(SignupPage);
