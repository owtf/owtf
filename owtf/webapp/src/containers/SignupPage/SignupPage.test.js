import React from "react";
import { shallow } from "enzyme";
import toJson from "enzyme-to-json";
import "../../setupTests";
import { findByTestAtrr, checkProps } from "../../utils/testUtils";
import { SignupPage } from "./index";
import { fromJS } from "immutable";

import { signupFail, signupSuccess } from "./actions";
import { emailSendStart } from "../EmailVerification/actions";
import { SIGNUP_START, SIGNUP_SUCCESS, SIGNUP_FAIL } from "./constants";

import { postDataToSignupAPI } from "./saga";
import { runSaga } from "redux-saga";
import * as api from "./api";

import { signupReducer } from "./reducer";

describe("SignupPage component", () => {
  describe("Testing dumb signup page component", () => {
    let wrapper;
    let props;

    beforeEach(() => {
      props = {
        onSignup: jest.fn()
      };
      wrapper = shallow(<SignupPage {...props} />);
    });

    it("Should have correct prop-types", () => {
      const expectedProps = {
        onSignup: () => {}
      };
      const propsErr = checkProps(SignupPage, expectedProps);
      expect(propsErr).toBeUndefined();
    });

    it("Should render without errors", () => {
      const component = findByTestAtrr(wrapper, "signupPageComponent");
      expect(component.length).toBe(1);
      expect(toJson(component)).toMatchSnapshot();
    });

    it("Should correctly render its sub-components", () => {
      wrapper.setState({
        username: "test_user",
        email: "test_user@test.com",
        password: "Test@1234",
        confirmPassword: "Test@1234",
        errors: {},
        hidePassword: true,
        hideConfirmPassword: true
      });
      const heading = wrapper.find("h2");
      const textInputField = wrapper.find("input");
      const paragraph = wrapper.find("p");
      const button = wrapper.find("button");

      expect(heading.length).toBe(1);
      expect(heading.at(0).props().children).toEqual("Create an OWTF Account");
      expect(textInputField.length).toBe(4);
      expect(textInputField.at(0).props().placeholder).toEqual("Username");
      expect(textInputField.at(1).props().placeholder).toEqual("Email");
      expect(textInputField.at(2).props().placeholder).toEqual("Password");
      expect(textInputField.at(3).props().placeholder).toEqual(
        "Confirm Password"
      );
      expect(paragraph.length).toBe(4);
      expect(button.length).toBe(1);
      expect(button.at(0).props().children).toEqual("SIGNUP");
      expect(button.at(0).props().disabled).toEqual(false);
    });

    it("Should update state on TextInputField change event", () => {
      const textInputFieldUsername = wrapper.find("input").at(0);
      const eventChangeUsername = {
        preventDefault() {},
        target: { value: "test_user1", name: "text-input-name" }
      };
      textInputFieldUsername.simulate("change", eventChangeUsername);
      expect(wrapper.instance().state.username).toEqual("test_user1");

      const textInputFieldEmail = wrapper.find("input").at(1);
      const eventChangeEmail = {
        preventDefault() {},
        target: { value: "test_user@test.com", name: "text-input-email" }
      };
      textInputFieldEmail.simulate("change", eventChangeEmail);
      expect(wrapper.instance().state.email).toEqual("test_user@test.com");

      const textInputFieldPassword = wrapper.find("input").at(2);
      const eventChangePassword = {
        preventDefault() {},
        target: { value: "Test@12345", name: "text-input-password" }
      };
      textInputFieldPassword.simulate("change", eventChangePassword);
      expect(wrapper.instance().state.password).toEqual("Test@12345");

      const textInputFieldConfirmPassword = wrapper
        .find("input")
        .at(3);
      const eventChangeConfirmPassword = {
        preventDefault() {},
        target: { value: "Test@12345", name: "text-input-confirm-password" }
      };
      textInputFieldConfirmPassword.simulate(
        "change",
        eventChangeConfirmPassword
      );
      expect(wrapper.instance().state.confirmPassword).toEqual("Test@12345");
    });

    it("Should call onSignup on signup button click", () => {
      expect(props.onSignup.mock.calls.length).toBe(0);
      const signupButton = wrapper.find("button");
      signupButton.simulate("click");
      expect(props.onSignup.mock.calls.length).toBe(1);
    });
  });

  describe("Testing the sagas", () => {
    describe("Testing postDataToSignupAPI saga", () => {
      let fakeAction;
      beforeEach(() => {
        fakeAction = {
          type: SIGNUP_START,
          email: "test_user@test.com"
        };
      });

      it("Should create an user in case of success", async () => {
        const successData = {
          status: "success",
          data: { status: "success", message: "User created successfully" }
        };

        const dispatchedActions = [];
        api.signupUsingSignupAPI = jest.fn(() =>
          jest.fn(() => Promise.resolve(successData))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postDataToSignupAPI, fakeAction).done;
        expect(api.signupUsingSignupAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(
          signupSuccess(successData["data"]["message"], fakeAction["email"])
        );
        expect(dispatchedActions).toContainEqual(
          emailSendStart(fakeAction["email"])
        );
      });

      it("Should handle signup create error in case of failure", async () => {
        const dispatchedActions = [];
        const error = "API server is down";
        api.signupUsingSignupAPI = jest.fn(() =>
          jest.fn(() => Promise.reject(error))
        );

        const fakeStore = {
          getState: () => ({ state: "test" }),
          dispatch: action => dispatchedActions.push(action)
        };

        await runSaga(fakeStore, postDataToSignupAPI, fakeAction).done;
        expect(api.signupUsingSignupAPI.mock.calls.length).toBe(1);
        expect(dispatchedActions).toContainEqual(signupFail(error));
      });
    });
  });

  describe("Testing reducers", () => {
    describe("Testing signupReducer", () => {
      let initialState;
      beforeEach(() => {
        initialState = {
          error: false,
          loading: false,
          email: null
        };
      });

      it("Should return the initial state", () => {
        const newState = signupReducer(undefined, {});
        expect(newState.toJS()).toEqual(initialState);
      });

      it("Should handle SIGNUP_START", () => {
        const newState = signupReducer(undefined, {
          type: SIGNUP_START
        });

        expect(newState.toJS()).toEqual({
          loading: true,
          error: false,
          email: null
        });
      });

      it("Should handle SIGNUP_SUCCESS", () => {
        const email = "test_email@test.com";
        const newState = signupReducer(
          fromJS({
            loading: true,
            error: true,
            email: null
          }),
          {
            type: SIGNUP_SUCCESS,
            email: email
          }
        );

        expect(newState.toJS()).toEqual({
          loading: false,
          error: false,
          email: email
        });
      });

      it("Should handle SIGNUP_FAIL", () => {
        const err = "Test sessions loading error";
        const newState = signupReducer(
          fromJS({
            loading: true,
            error: true,
            email: null
          }),
          {
            type: SIGNUP_FAIL,
            error: err
          }
        );

        expect(newState.toJS()).toEqual({
          loading: false,
          error: err,
          email: null
        });
      });
    });
  });
});
