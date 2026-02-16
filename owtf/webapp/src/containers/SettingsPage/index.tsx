/*
 * SettingsPage
 * Neutral shadcn/tailwind configuration editor.
 */
import React from "react";
import { connect } from "react-redux";
import { createStructuredSelector } from "reselect";
import { AlertCircle, Save } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "../../components/ui/alert";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Spinner } from "../../components/ui/spinner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../../components/ui/tabs";
import { changeConfigurations, loadConfigurations } from "./actions";
import {
  makeSelectChangeError,
  makeSelectFetchConfigurations,
  makeSelectFetchError,
  makeSelectFetchLoading,
} from "./selectors";

type SettingItem = {
  key: string;
  value: string;
  descrip: string;
};

interface PropsType {
  loading: boolean;
  fetchError: object | boolean;
  changeError: object | boolean;
  configurations: Record<string, SettingItem[]> | boolean;
  onFetchConfiguration: Function;
  onChangeConfiguration: Function;
}

interface StateType {
  updateDisabled: boolean;
  patch_data: Record<string, string>;
  show: boolean;
  selectedTab: string;
}

export class SettingsPage extends React.Component<PropsType, StateType> {
  constructor(props) {
    super(props);
    this.state = {
      updateDisabled: true,
      patch_data: {},
      show: false,
      selectedTab: "",
    };
  }

  componentDidMount() {
    this.props.onFetchConfiguration();
  }

  componentDidUpdate(prevProps: PropsType) {
    if (this.props.configurations !== prevProps.configurations && this.props.configurations !== false) {
      const sections = Object.keys(this.props.configurations);
      if (sections.length > 0 && !this.state.selectedTab) {
        this.setState({ selectedTab: sections[0] });
      }
    }
  }

  onUpdateConfiguration = () => {
    this.props.onChangeConfiguration(this.state.patch_data);
    this.setState({
      patch_data: {},
      updateDisabled: true,
      show: true,
    });

    setTimeout(() => {
      this.setState({ show: false });
    }, 3000);
  };

  handleConfigurationChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = event.target;
    this.setState((state) => ({
      patch_data: { ...state.patch_data, [name]: value },
      updateDisabled: false,
    }));
  };

  renderAlert(error: any) {
    if (!this.state.show) {
      return null;
    }

    if (error !== false) {
      return (
        <Alert variant="danger">
          <AlertTitle>Update failed</AlertTitle>
          <AlertDescription>{String(error)}</AlertDescription>
        </Alert>
      );
    }

    return (
      <Alert variant="success">
        <AlertTitle>Configuration updated</AlertTitle>
        <AlertDescription>Your settings have been saved.</AlertDescription>
      </Alert>
    );
  }

  renderSettingsContent(configurations: Record<string, SettingItem[]>) {
    const sections = Object.keys(configurations);
    const currentTab = this.state.selectedTab || sections[0] || "";

    if (!sections.length) {
      return <p className="text-sm text-zinc-500">No settings available.</p>;
    }

    return (
      <Tabs value={currentTab} onValueChange={(value) => this.setState({ selectedTab: value })}>
        <TabsList className="h-auto flex-wrap justify-start gap-1">
          {sections.map((section) => (
            <TabsTrigger key={section} value={section} className="capitalize">
              {section.replace(/_/g, " ")}
            </TabsTrigger>
          ))}
        </TabsList>

        {sections.map((section) => (
          <TabsContent key={section} value={section}>
            <Card className="border-zinc-200 bg-white/95 shadow-sm dark:border-zinc-800 dark:bg-zinc-900/80">
              <CardHeader>
                <CardTitle className="text-base capitalize">{section.replace(/_/g, " ")}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {(configurations[section] || []).map((config, index) => (
                  <div key={config.key || index} className="space-y-1.5">
                    <label
                      htmlFor={`${section}-${config.key}`}
                      className="text-xs font-medium uppercase tracking-wide text-zinc-500"
                    >
                      {config.key.replace(/_/g, " ")}
                    </label>
                    <Input
                      id={`${section}-${config.key}`}
                      type="text"
                      name={config.key}
                      defaultValue={config.value}
                      title={config.descrip}
                      onChange={this.handleConfigurationChange}
                    />
                    {config.descrip ? <p className="text-xs text-zinc-500">{config.descrip}</p> : null}
                  </div>
                ))}
              </CardContent>
            </Card>
          </TabsContent>
        ))}
      </Tabs>
    );
  }

  render() {
    const { configurations, loading, fetchError, changeError } = this.props;

    if (loading) {
      return (
        <div className="flex justify-center py-12">
          <Spinner size={32} />
        </div>
      );
    }

    if (fetchError !== false) {
      return (
        <div className="mx-auto w-full max-w-[1240px] px-4 py-6">
          <Alert variant="danger">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Settings load failed</AlertTitle>
            <AlertDescription>Something went wrong, please try again.</AlertDescription>
          </Alert>
        </div>
      );
    }

    if (configurations === false) {
      return null;
    }

    return (
      <div className="mx-auto w-full max-w-[1240px] space-y-6 px-4 py-6" data-test="settingsPageComponent">
        {this.renderAlert(changeError)}

        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-100">Settings</h1>
            <p className="text-sm text-zinc-600 dark:text-zinc-300">
              Review and update OWTF runtime configuration values.
            </p>
          </div>

          <Button disabled={this.state.updateDisabled} onClick={this.onUpdateConfiguration} data-test="changeBtn">
            <Save className="h-4 w-4" />
            Update Configuration
          </Button>
        </div>

        {this.renderSettingsContent(configurations as Record<string, SettingItem[]>)}
      </div>
    );
  }
}

const mapStateToProps = createStructuredSelector({
  configurations: makeSelectFetchConfigurations,
  loading: makeSelectFetchLoading,
  fetchError: makeSelectFetchError,
  changeError: makeSelectChangeError,
});

const mapDispatchToProps = (dispatch) => ({
  onFetchConfiguration: () => dispatch(loadConfigurations()),
  onChangeConfiguration: (patch_data) => dispatch(changeConfigurations(patch_data)),
});

//@ts-ignore
export default connect(mapStateToProps, mapDispatchToProps)(SettingsPage);
